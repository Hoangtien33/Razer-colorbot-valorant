import ctypes
import numpy as np
from ctypes import wintypes

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG), ('biHeight', wintypes.LONG),
                ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG), ('biYPelsPerMeter', wintypes.LONG),
                ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', wintypes.DWORD * 1)]

class DirectXCapture:
    def __init__(self):
        self.hdesktop = ctypes.windll.user32.GetDC(0)
        self.width = ctypes.windll.user32.GetSystemMetrics(0)
        self.height = ctypes.windll.user32.GetSystemMetrics(1)
        self.buffer_size = self.width * self.height * 4

        self.bitmap_info = BITMAPINFO()
        bmi = self.bitmap_info.bmiHeader
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = self.width
        bmi.biHeight = -self.height
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0
        bmi.biSizeImage = 0

        self._BitBlt = ctypes.windll.gdi32.BitBlt
        self._CreateCompatibleDC = ctypes.windll.gdi32.CreateCompatibleDC
        self._CreateDIBSection = ctypes.windll.gdi32.CreateDIBSection
        self._SelectObject = ctypes.windll.gdi32.SelectObject
        self._DeleteObject = ctypes.windll.gdi32.DeleteObject
        self._DeleteDC = ctypes.windll.gdi32.DeleteDC
        self._ReleaseDC = ctypes.windll.user32.ReleaseDC

        self.buffers = [self._create_buffer() for _ in range(2)]
        self.current = 0

    def _create_buffer(self):
        mem_dc = self._CreateCompatibleDC(self.hdesktop)
        ptr = ctypes.c_void_p()
        hbitmap = self._CreateDIBSection(self.hdesktop, ctypes.byref(self.bitmap_info), 0, ctypes.byref(ptr), None, 0)
        if not hbitmap:
            raise RuntimeError('CreateDIBSection failed!')
        self._SelectObject(mem_dc, hbitmap)
        np_frame = np.ctypeslib.as_array((ctypes.c_ubyte * self.buffer_size).from_address(ptr.value)).reshape((self.height, self.width, 4))
        return {'hdc': mem_dc, 'hbitmap': hbitmap, 'np_frame': np_frame}

    def capture_screen(self):
        buf = self.buffers[self.current]
        if not self._BitBlt(buf['hdc'], 0, 0, self.width, self.height, self.hdesktop, 0, 0, 0x00CC0020):
            raise RuntimeError('BitBlt failed!')
        frame = buf['np_frame'][:, :, :3].copy()
        self.current = (self.current + 1) % 2
        return frame

    def close(self):
        for buf in self.buffers:
            self._DeleteObject(buf['hbitmap'])
            self._DeleteDC(buf['hdc'])
        self._ReleaseDC(0, self.hdesktop)
