from shared.globals import TERMINAL_WIDTH
from colorama import Fore, Style

text_default = {
    'small': 'FOR TITLE OF SOME SMALL THING :>',
    'big': 'FOR TITLE OF BIGGER THING :>',
    'danger': 'HOLYYYY NOOOO~~ LET TRY AGAINNN',
    'success': 'YESSS~~ ITS WORKINGG',
    'exist': 'WAS CRAWLED BEFORE SO NEXTTTTTTT!!',
    'wait': 'WAITING.....'
}

def print_banner_colored(title: str = '', style='small'):
    title = title.upper() or text_default[style]

    size_max = TERMINAL_WIDTH

    match style:
        case 'small':
            banner = "─" * (TERMINAL_WIDTH // 2)

            print('\n')
            print(Fore.LIGHTRED_EX + f"╭{banner}╮".center(TERMINAL_WIDTH) + Style.RESET_ALL)
            print(Fore.MAGENTA + title.center(TERMINAL_WIDTH) + Style.RESET_ALL)
            print(Fore.LIGHTRED_EX + f"╰{banner}╯".center(TERMINAL_WIDTH) + Style.RESET_ALL)
        
        case 'big':
            banner = "─" * (TERMINAL_WIDTH - 2)

            print('\n')
            print(Fore.YELLOW + f"╭{banner}╮".center(TERMINAL_WIDTH) + Style.RESET_ALL  + '\n')
            print(Fore.GREEN + f"║{title.center(TERMINAL_WIDTH - 2)}║" + Style.RESET_ALL  + '\n')
            print(Fore.YELLOW + f"╰{banner}╯".center(TERMINAL_WIDTH) + Style.RESET_ALL)

        case 'danger':
            title = '────── ⛔ ' + title + ' ⛔ ──────'
            print(Fore.RED + title.center(size_max) + Style.RESET_ALL)

        case 'success':
            title = '────── 🎉 ' + title + ' 🎉 ──────'
            print(Fore.GREEN + title.center(size_max) + Style.RESET_ALL)
        
        case 'exist':
            title = '────── 👌 ' + title + '👌 ──────'
            print(Fore.YELLOW + title.center(size_max) + Style.RESET_ALL)

        case 'wait':
            title = '────── ⏰ ' + title + ' ⏰ ──────'
            print(Fore.CYAN + title.center(size_max) + Style.RESET_ALL)


# Sử dụng:
# if __name__ == '__main__':
    # print("BIG STYLE : ")
    # print_banner_colored("", 'big')

    # print("SMALL STYLE : ")
    # print_banner_colored("", 'small')

    # print('DANGER STYLE : ')
    # print_banner_colored("", 'danger')

    # print('DANGER STYLE : ')
    # print_banner_colored("", 'success')

    # reset_previous_crawl()
