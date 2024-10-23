import argparse
import sys
import os
import generateParametricInput


def parseArguments():
    """
    Parse command-line arguments.
    
    Returns:
    argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Framework for a Python script with command-line arguments.")
    
    # Example argument
    parser.add_argument("-f", "--file", type=str, help="Track file")
    
    # You can add more arguments here as needed
    
    return parser.parse_args()

def entryPoint():
    """
    Entry point of the script. Handles setup and teardown.
    """
    try:
        args = parseArguments()
        main(args)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    
def main(args):
    generateParametricInput.main(args.file)
    
if __name__ == "__main__":
    entryPoint()