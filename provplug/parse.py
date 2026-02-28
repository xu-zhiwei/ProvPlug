import argparse
from parser import parse


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='mode', required=True)
    
    darpa = subparsers.add_parser('darpa_e3')
    darpa.add_argument('--data-files', nargs='+', required=True)
    darpa.add_argument('--edge-files', nargs='+', required=True)
    
    optc = subparsers.add_parser('optc')
    optc.add_argument('--input-filename', required=True)
    optc.add_argument('--output-filename', required=True)
    
    args = parser.parse_args()
    
    if args.mode == 'darpa_e3':
        parse(
            mode='darpa_e3',
            data_files=args.data_files,
            edge_files=args.edge_files
        )
    elif args.mode == 'optc':
        parse(
            mode='optc',
            input_filename=args.input_filename,
            output_filename=args.output_filename
        )


if __name__ == '__main__':
    main()
