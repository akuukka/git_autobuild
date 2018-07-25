import time
import signal
import sys
import os
import json
import subprocess

config = None
quit = False

def signal_handler(signal, frame):
    global quit
    print("Requesting quit...")
    quit = True

def init():
    print("Initializing...")
    data = { "last_hash": 0 }
    with open('.git_autobuild', 'w') as outfile:
        json.dump(data, outfile)
    outfile.close()

    # Clone the repo
    cmd = "git clone " + config["repo"]
    res = os.system(cmd)

def get_last_processed_hash():
    outfile = open('.git_autobuild', 'r')
    data = json.load(outfile)
    outfile.close()
    return str(data["last_hash"])

def get_repo_dir():
    dirlist = os.listdir(".")
    for dir in dirlist:
        if dir in config["repo"]:
            return dir
    print("Could not find repo dir")
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
    os.system(config["run_cmd"])
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
    global config
    try:
        outfile = open('config.json', 'r')
        config = json.load(outfile)
        outfile.close()
    except FileNotFoundError:
        print("config.json not present.")
        exit(2)

if __name__ == "__main__":
    read_config()
    
    signal.signal(signal.SIGINT, signal_handler)

    print("Starting git-autobuild")

    wd = config["working_dir"]

    # TODO: if clean is requested, should remove the working directory if it exists    
    if not os.path.exists(wd):
        os.mkdir(wd)

    os.chdir(wd)
    if not os.path.exists(".git_autobuild"):
        init()

    update_interval = config["update_interval"]
    while not quit:
        do_pull()
        
        last_processed_hash = get_last_processed_hash()
        current_hash = get_current_hash()
        if last_processed_hash != current_hash:
            print("Top commit changed - trigger build")
            process_repo(current_hash)
            
        time.sleep(update_interval)
    
