"""Console script for toutiao."""

import fire


def help():
    print("toutiao")
    print("=" * len("toutiao"))
    print("Skeleton project created by Python Project Wizard (ppw)")


def main():
    fire.Fire({"help": help})


if __name__ == "__main__":
    main()  # pragma: no cover
