"""
A simple git repo autobuilder
"""

import shutil
import time
import signal
import sys
import os
import json
import subprocess
import optparse

CONFIG = {}
QUIT = False

def signal_handler(signal, frame):
    global QUIT
    print("Requesting quit...")
    QUIT = True

def init():
    print("Initializing...")
    data = { "last_hash": 0 }
    with open('.git_autobuild', 'w') as outfile:
        json.dump(data, outfile)
    outfile.close()

    # Clone the repo
    cmd = "git clone " + CONFIG["repo"]
    res = os.system(cmd)

def get_last_processed_hash():
    outfile = open('.git_autobuild', 'r')
    data = json.load(outfile)
    outfile.close()
    return str(data["last_hash"])

def get_repo_dir():
    dirlist = os.listdir(".")
    for dir in dirlist:
        if dir in CONFIG["repo"]:
            return dir
    sys.stderr.write("Could not find repo dir")
    exit(2)

def get_current_hash():
    repo_dir = get_repo_dir()
    os.chdir(repo_dir)
    os.system("git rev-parse HEAD > ../.hash_temp")
    os.chdir("..")

    hash_file = open(".hash_temp", 'r')
    hash_str = hash_file.read().strip()
    hash_file.close()
    return hash_str

def do_pull():
    repo_dir = get_repo_dir()
    os.chdir(repo_dir)
    subprocess.check_output('git pull', shell=True)
    os.chdir("..")

def process_repo(new_hash):
    repo_dir = get_repo_dir()
    os.chdir(repo_dir)
    os.system(CONFIG["run_cmd"])
    os.chdir("..")

    # Update processed hash
    outfile = open('.git_autobuild', 'r')
    data = json.load(outfile)
    outfile.close()
    data["last_hash"] = new_hash
    with open('.git_autobuild', 'w') as outfile:
        json.dump(data, outfile)
    outfile.close()

def read_config():
    try:
        outfile = open('config.json', 'r')
        config = json.load(outfile)
        outfile.close()
    except FileNotFoundError:
        sys.stderr.write("config.json not present.")
        exit(2)
    return config

def main_loop():
    parser = optparse.OptionParser()
    parser.add_option("-c", "--clean", action="store_true", default=False, dest="clean",
                      help="Clean everything before generating the projects")
    parser.add_option("-r", "--rerun_cmd", action="store_true", default=False, dest="rerun_cmd",
                      help="Re-runs the command specified in config.json even if git latest commit hash has not changed since the command was run last time.")
    (options, _) = parser.parse_args()

    # Perform clean if requested: meaning that we will clone the repo again
    if options.clean:
        if os.path.exists(CONFIG["working_dir"]):
            shutil.rmtree(CONFIG["working_dir"])
    
    if not os.path.exists(CONFIG["working_dir"]):
        os.mkdir(CONFIG["working_dir"])

    os.chdir(CONFIG["working_dir"])
    if not os.path.exists(".git_autobuild"):
        init()

    update_interval = CONFIG["update_interval"]
    while not QUIT:
        do_pull()
        last_processed_hash = get_last_processed_hash()
        current_hash = get_current_hash()
        if last_processed_hash != current_hash or options.rerun_cmd:
            options.rerun_cmd = False
            process_repo(current_hash)
        time.sleep(update_interval)

if __name__ == "__main__":
    CONFIG = read_config()
    signal.signal(signal.SIGINT, signal_handler)
    main_loop()
    
