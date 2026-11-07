from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
import xml.etree.ElementTree as ET
BASE = "https://physionet-open.s3.amazonaws.com/"
KEY_PREFIX = "challenge-2019/1.0.0/"
ROOT = Path(__file__).resolve().parents[1] / ".tools" / "physionet-challenge-2019"
NS = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}
def list_objects(prefix):
    keys=[]; token=None
    while True:
        params={"list-type":"2", "prefix":prefix, "max-keys":"1000"}
        if token: params["continuation-token"]=token
        with urlopen(BASE+"?"+urlencode(params),timeout=60) as response: root=ET.fromstring(response.read())
        keys.extend(item.findtext("s:Key",namespaces=NS) for item in root.findall("s:Contents",NS))
        if root.findtext("s:IsTruncated",namespaces=NS)!="true": return keys
        token=root.findtext("s:NextContinuationToken",namespaces=NS)
def enumerate_files():
    return [key for key in list_objects(KEY_PREFIX) if not key.endswith("/")]
def fetch(key):
    relative=key.removeprefix(KEY_PREFIX); target=ROOT/relative; target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() and target.stat().st_size: return target.stat().st_size
    temp=target.with_suffix(target.suffix+".part")
    with urlopen(BASE+key,timeout=60) as response,temp.open("wb") as output:
        while chunk:=response.read(1024*1024): output.write(chunk)
    temp.replace(target); return target.stat().st_size
for partial in ROOT.rglob("*.part") if ROOT.exists() else []: partial.unlink()
keys=enumerate_files(); print(f"Downloading {len(keys)} public objects via PhysioNet's documented anonymous S3 mirror",flush=True)
total=0;done=0
with ThreadPoolExecutor(max_workers=48) as pool:
    for future in as_completed([pool.submit(fetch,key) for key in keys]):
        total+=future.result();done+=1
        if done%500==0 or done==len(keys): print(f"Completed {done}/{len(keys)}; {total} bytes",flush=True)
print(f"Download complete: {done} files, {total} bytes",flush=True)
