"""
File management utilities for the lead generation pipeline
"""
import os
import time
import logging
import shutil
from pathlib import Path
from datetime import datetime

class FileManager:
    """Manages file organization for the lead generation pipeline"""
    
    def __init__(self, base_dir="output"):
        """Initialize with base output directory"""
        self.base_dir = Path(base_dir)
        self.timestamp = time.strftime('%Y%m%d_%H%M%S')
        self.run_dir = None
        self.setup_directories()
    
    def setup_directories(self):
        """Set up organized directory structure"""
        # Create main output directory if it doesn't exist
        self.base_dir.mkdir(exist_ok=True)
        
        # Create run-specific directory
        self.run_dir = self.base_dir / f"run_{self.timestamp}"
        self.run_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.run_dir / "linkedin").mkdir(exist_ok=True)
        (self.run_dir / "apollo").mkdir(exist_ok=True)
        (self.run_dir / "merged").mkdir(exist_ok=True)
        (self.run_dir / "processed").mkdir(exist_ok=True)
        (self.run_dir / "screenshots").mkdir(exist_ok=True)
        
        logging.info(f"Created organized directory structure in {self.run_dir}")
    
    def get_linkedin_path(self, filename=None):
        """Get path for LinkedIn output files"""
        if filename:
            return self.run_dir / "linkedin" / filename
        return self.run_dir / "linkedin" / f"linkedin_leads_{self.timestamp}.csv"
    
    def get_apollo_path(self, filename=None):
        """Get path for Apollo output files"""
        if filename:
            return self.run_dir / "apollo" / filename
        return self.run_dir / "apollo" / f"apollo_leads_{self.timestamp}.csv"
    
    def get_merged_path(self, filename=None):
        """Get path for merged output files"""
        if filename:
            return self.run_dir / "merged" / filename
        return self.run_dir / "merged" / f"merged_leads_{self.timestamp}.csv"
    
    def get_processed_path(self, source="merged", filename=None):
        """Get path for processed output files"""
        if filename:
            return self.run_dir / "processed" / filename
        return self.run_dir / "processed" / f"{source}_processed_{self.timestamp}.csv"
    
    def get_screenshot_path(self, name):
        """Get path for screenshot files"""
        return self.run_dir / "screenshots" / f"{name}_{self.timestamp}.png"
    
    def save_latest_reference(self, filepath, type_label):
        """Create a reference to the latest file of a particular type"""
        reference_file = self.base_dir / f"latest_{type_label}.txt"
        with open(reference_file, "w") as f:
            f.write(str(filepath))
        logging.info(f"Updated reference to latest {type_label} file: {filepath}")
    
    def get_latest_file(self, type_label):
        """Get the latest file of a particular type"""
        reference_file = self.base_dir / f"latest_{type_label}.txt"
        if reference_file.exists():
            with open(reference_file, "r") as f:
                return Path(f.read().strip())
        return None
    
    def cleanup_old_runs(self, keep_last=5):
        """Cleanup old run directories, keeping the most recent ones"""
        # Get all run directories
        run_dirs = [d for d in self.base_dir.iterdir() 
                   if d.is_dir() and d.name.startswith("run_")]
        
        # Sort by creation time (newest first)
        run_dirs.sort(key=lambda d: d.stat().st_ctime, reverse=True)
        
        # Remove older directories beyond the keep limit
        if len(run_dirs) > keep_last:
            for old_dir in run_dirs[keep_last:]:
                logging.info(f"Cleaning up old run directory: {old_dir}")
                try:
                    shutil.rmtree(old_dir)
                except Exception as e:
                    logging.warning(f"Error cleaning up directory {old_dir}: {e}")