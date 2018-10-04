from straitjacket import sjfmt
import black
import blackd

sjfmt.patch_format_str()
main = blackd.main


if __name__ == '__main__':
    black.patch_click()
    main()
