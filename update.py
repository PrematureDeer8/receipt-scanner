import hashlib
import pathlib
import urllib3
import re
import subprocess
import eel

class Update:
    def __init__(self,vCurrent):
        self.http = urllib3.PoolManager();
        self.vCurrent = vCurrent;
        self.path = pathlib.Path(r"C:\ProgramData\Receipt-Scanner\setup-exes");
        setup = self.path / "setup.exe"
        self.path.mkdir(parents=True, exist_ok=True);
        setup.unlink(missing_ok=True);                  
        self.our_hash = None;
        self.version = None;
    def download(self, exe="mysetup.exe"):
        hash = hashlib.sha256();
        request = self.http.request(
            "GET",
            f"https://github.com/PrematureDeer8/receipt-scanner/releases/download/{self.version}/{exe}",
            preload_content=False
        );
        # write exe
        setup = self.path / "setup.exe"
        with open(setup, "wb") as exe:
            # write exe chunk by chunk so that ram doesn't overload
            for chunk in request.stream(4096):
                hash.update(chunk);
                exe.write(chunk);
            request.release_conn();
        # check if setup.exe is really ours
        if(hash.hexdigest() == self.our_hash):
            # run our exe
            eel.close();
            subprocess.Popen(setup.absolute());
        else:
            # delete our fake exe
            setup.unlink();
            eel.error_message({"Exists": True, "message": "Couldn't verify the exe! Update stopped!"})
    def updateAvailable(self):
        request = self.http.request(
            "GET",
            "https://github.com/PrematureDeer8/receipt-scanner/releases/latest"
        );
        possible_versions = re.findall("v\d+.\d+.\d+", str(request.data));
        # get the most common version 
        self.version = max(set(possible_versions), key=possible_versions.count);
        # I.G. version = v2.1.0 vCurrent = v2.0.0  find the max 
        # update our application if true
        if(max(self.version, self.vCurrent) == self.version 
           and not(self.version == self.vCurrent)):
            request = self.http.request("GET", 
            f"https://raw.githubusercontent.com/PrematureDeer8/receipt-scanner/master/hash/{self.version}.txt"
            );
            self.our_hash = request.data.decode("UTF-8");
            if("404: Not found".upper() in self.our_hash.upper()):
                # eel.error_message({"Exists": True, "message": "Could not find exe version!"});
                return False;
            return True;
        else:
            return False;