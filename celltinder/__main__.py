import sys
from pathlib import Path

from celltinder import run_cell_tinder

def main() -> None:
    """
    Main entry point for the CellTinder application.
    """
    if len(sys.argv) < 2:
        print("Usage: python -m celltinder <csv_path> [n_frames] [crop_size]")
        sys.exit(1)
        
    csv_path = Path(sys.argv[1])
    n_frames = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    crop_size = int(sys.argv[3]) if len(sys.argv) > 3 else 151
    run_cell_tinder(csv_path, n_frames, crop_size)
    
if __name__ == "__main__":
    main()