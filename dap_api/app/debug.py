import uvicorn
import subprocess
import os

if __name__ == '__main__':

    # run pre-start script
    my_env = os.environ.copy()
    my_env["PATH"] = "/usr/sbin:/sbin:" + my_env["PATH"]
    subprocess.call(['sh', './prestart.sh'], env=my_env)

    # start fastapi app
    uvicorn.run("app.main:app",
                host="0.0.0.0",
                port=8082,
                log_level="debug",
                reload=True,
                reload_dirs=[os.getcwd()])
