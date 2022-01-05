import pstats
import pathlib

HERE = pathlib.Path(__file__).absolute().parent


def main(path: pathlib.Path):
    p = pstats.Stats(str(path))
    p.strip_dirs().sort_stats('cumulative').print_stats(100)


if __name__ == '__main__':
    main(HERE / 'profile.txt')
