from colorama import Fore

def print_banner():
    print(Fore.YELLOW + "\n====================================")
    print(Fore.YELLOW + "     Donna Aimbot")
    print(Fore.YELLOW + "====================================")
    print(Fore.YELLOW + " __   __  __  _ __  _  __   ")
    print(Fore.YELLOW + "| _\\ /__\\|  \\| |  \\| |/  \\  ")
    print(Fore.YELLOW + "| v | \\/ | | ' | | ' | /\\ | ")
    print(Fore.YELLOW + "|__/ \\__/|_|\\__|_|\\__|_||_| ")
    print(Fore.YELLOW + "====================================")
    print(Fore.GREEN + " Source: " + Fore.WHITE + "VuDungVapeV4")
    print(Fore.GREEN + " Discord: " + Fore.WHITE + "https://discord.gg/vfWYhwA9Uz")
    print(Fore.GREEN + " Updated by: " + Fore.WHITE + "MacusExciuci")
    print(Fore.GREEN + " Discord: " + Fore.WHITE + "discord.gg/yX3wXZWqMx")
    print(Fore.YELLOW + "====================================")
    print(Fore.CYAN + " Press F5 to reload config")
    print(Fore.YELLOW + "====================================\n")

def print_config(cfg):
    from pprint import pprint
    print(Fore.CYAN + "[CONFIG LOADED]")
    pprint(cfg)
    print()
