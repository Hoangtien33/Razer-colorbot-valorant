import ctypes
from ctypes import *
from ctypes.wintypes import *
from typing import Tuple
from logger import logger

ntdll = windll.ntdll
kernel32 = windll.kernel32

INVALID_HANDLE_VALUE = c_void_p(-1).value
FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2
OPEN_EXISTING = 3
DIRECTORY_QUERY = 1
OBJ_CASE_INSENSITIVE = 64
NTSTATUS = c_long
STATUS_BUFFER_TOO_SMALL = NTSTATUS(0xC0000023).value
STATUS_NO_MORE_ENTRIES = 0x8000001A
PVOID = c_void_p
PWSTR = c_wchar_p
IOCTL_MOUSE = 0x22200C

class UNICODE_STRING(Structure):
    _fields_ = [('Length', USHORT), ('MaximumLength', USHORT), ('Buffer', PWSTR)]

class OBJECT_ATTRIBUTES(Structure):
    _fields_ = [('Length', ULONG), ('RootDirectory', HANDLE), ('ObjectName', POINTER(UNICODE_STRING)),
                ('Attributes', ULONG), ('SecurityDescriptor', PVOID), ('SecurityQualityOfService', PVOID)]

class OBJECT_DIRECTORY_INFORMATION(Structure):
    _fields_ = [('Name', UNICODE_STRING), ('TypeName', UNICODE_STRING)]

class RZCONTROL_IOCTL_STRUCT(Structure):
    _fields_ = [
        ('unk0', c_int32),
        ('unk1', c_int32),
        ('max_val_or_scan_code', c_int32),
        ('click_mask', c_int32),
        ('unk3', c_int32),
        ('x', c_int32),
        ('y', c_int32),
        ('unk4', c_int32)
    ]

def get_screen_resolution():
    user32 = windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

def InitializeObjectAttributes(attrs, name, flags, root, sd):
    memset(addressof(attrs), 0, sizeof(attrs))
    attrs.Length = sizeof(attrs)
    attrs.ObjectName = name
    attrs.Attributes = flags
    attrs.RootDirectory = root
    attrs.SecurityDescriptor = sd
    attrs.SecurityQualityOfService = None

def RtlInitUnicodeString(dst, src):
    if not isinstance(src, (str, bytes)):
        raise ValueError("src must be a string or bytes")
    memset(addressof(dst), 0, sizeof(dst))
    if isinstance(src, str):
        src = src.encode('utf-16-le')
    dst.Buffer = cast(src, PWSTR)
    dst.Length = len(src)
    dst.MaximumLength = dst.Length + 2

def open_directory(root_handle, path, access):
    handle = c_void_p()
    uni_string = UNICODE_STRING()
    obj_name = None
    if path:
        buffer = create_unicode_buffer(path)
        RtlInitUnicodeString(uni_string, buffer)
        obj_name = pointer(uni_string)
    attrs = OBJECT_ATTRIBUTES()
    InitializeObjectAttributes(attrs, obj_name, OBJ_CASE_INSENSITIVE, root_handle, None)
    status = ntdll.NtOpenDirectoryObject(byref(handle), access, byref(attrs))
    if status != 0:
        raise RuntimeError(f'NtOpenDirectoryObject failed: 0x{status:X}')
    return handle.value

def find_sym_link(dir: str, name: str) -> Tuple[bool, str]:
    dir_handle = open_directory(None, dir, DIRECTORY_QUERY)
    if not dir_handle:
        raise RuntimeError(f"Failed to open directory '{dir}'.")
    query_context = ULONG(0)
    found = False
    out = None
    try:
        while True:
            length = ULONG()
            status = ntdll.NtQueryDirectoryObject(dir_handle, None, 0, True, False, byref(query_context), byref(length))
            if status == STATUS_NO_MORE_ENTRIES:
                break
            if status != STATUS_BUFFER_TOO_SMALL:
                raise RuntimeError(f'NtQueryDirectoryObject failed (initial call), status=0x{status:X}')
            buf = create_string_buffer(length.value)
            status = ntdll.NtQueryDirectoryObject(dir_handle, buf, length.value, True, False, byref(query_context), byref(length))
            if status not in (0, STATUS_NO_MORE_ENTRIES):
                raise RuntimeError(f'NtQueryDirectoryObject second call failed, status=0x{status:X}')
            objinf = cast(buf, POINTER(OBJECT_DIRECTORY_INFORMATION)).contents
            name_buf = objinf.Name.Buffer
            if name_buf:
                current_name = wstring_at(name_buf, objinf.Name.Length // 2)
                if name in current_name:
                    found = True
                    out = current_name
                    break
    finally:
        ntdll.NtClose(dir_handle)
    return (found, out)

class RZCONTROL:
    hDevice = INVALID_HANDLE_VALUE

    def __init__(self):
        try:
            self.init()
        except Exception as e:
            logger.error(f"❌ Không thể khởi tạo driver: {e}")
            RZCONTROL.hDevice = INVALID_HANDLE_VALUE

    def init(self):
        if RZCONTROL.hDevice != INVALID_HANDLE_VALUE:
            kernel32.CloseHandle(RZCONTROL.hDevice)

        sym_link_found, sym_link = find_sym_link('\\GLOBAL??', 'RZCONTROL')
        if not sym_link_found:
            raise RuntimeError('Không tìm thấy symbolic link RZCONTROL – Bạn đã inject driver chưa?')

        device_path = r'\\\\?\\' + sym_link
        RZCONTROL.hDevice = kernel32.CreateFileW(
            device_path,
            0,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            0,
            None
        )

        if RZCONTROL.hDevice == INVALID_HANDLE_VALUE:
            raise RuntimeError(f"❌ Mở thiết bị driver thất bại: {kernel32.GetLastError()}")
        return True

    def is_connected(self) -> bool:
        return RZCONTROL.hDevice != INVALID_HANDLE_VALUE


    def impl_mouse_ioctl(self, ioctl_struct):
        ioctl_ptr = pointer(ioctl_struct)
        bytes_returned = c_ulong()
        if not kernel32.DeviceIoControl(RZCONTROL.hDevice, IOCTL_MOUSE, ioctl_ptr, sizeof(ioctl_struct), None, 0, byref(bytes_returned), None):
            self.init()

    def mouse_move(self, x: float, y: float, speed: float, from_start: bool):
        if speed <= 0:
            raise ValueError("Speed must be > 0")
        screen_width, screen_height = get_screen_resolution()
        max_val = max(screen_width, screen_height)
        x = max(1, min(x, screen_width)) if not from_start else x
        y = max(1, min(y, screen_height)) if not from_start else y
        steps = min(int(speed), 10)
        delta_x = int(x / steps) if speed else 0
        delta_y = int(y / steps) if speed else 0
        struct = RZCONTROL_IOCTL_STRUCT(unk0=0, unk1=0, max_val_or_scan_code=max_val, click_mask=0, unk3=0, x=delta_x, y=delta_y, unk4=0)
        for _ in range(steps):
            self.impl_mouse_ioctl(struct)

    def __del__(self):
        if RZCONTROL.hDevice != INVALID_HANDLE_VALUE:
            kernel32.CloseHandle(RZCONTROL.hDevice)
            RZCONTROL.hDevice = INVALID_HANDLE_VALUE
