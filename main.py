import sys

def main():
    if "--gui" in sys.argv:
        try:
            from gui import launch
        except ImportError:
            print("GUI not implemented yet.")
            return
        launch()
    else:
        from cli import main as cli_main
        cli_main()

if __name__ == "__main__":
    main()