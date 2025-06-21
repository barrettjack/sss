## Shamir secret sharing library + standalone application written in python.

### **DISCLAIMER:**
**I am not a cybersecurity expert, nor am I a cryptography expert. I make absolutely no guarentees about the correctness or security of the implementation provided here. As such, I take no responsibility for losses incurred as a result of using this library/app. Don't roll your own crypto, as they say... You have been warned with abundant clarity and in no uncertain terms!**

### Motivation

I thought it would be fun to play around with implementing Shamir's secret sharing scheme in python, having learned about the scheme in UVic's course on cryptography. It is a simple and elegant (yet secure) scheme, which I invite you to appreciate by checking out the source code, and/or by reading about the scheme on [Wikipedia](https://en.wikipedia.org/wiki/Shamir%27s_secret_sharing).

### Practical utility

The practical utility of this scheme is that it provides a means to "break down" a key into shares without comprimising the security of the key that the shares protect. More concretely, you could take a key you wish to protect (say the backup key for your password manager) and split it into 3 shares such that:
- 2 of the 3 shares are required to recover the key.
- an attacker is in no better a position with 1 share than he is with 0 shares. (If an attacker comprimizes fewer than the threshold number of shares, he has not learned any information about the key.)

### Recommended setup procedure

Setup for the application should be quick and painless:
1) It is recommended that you set up a Python virtual environment in the working directory where `sss.py` lives so that the needed dependencies can be installed at specific versions. To do so, run `python3 -m venv venv` in the same directory that `sss.py` lives in.
2) Run `pip` to install the needed dependencies at the specified versions: `pip install -r requirements.txt`.
3) If you are a mac user, you may need also need to install `zbar` for full functionality. To do so, it is recommended that zbar be installed using `brew` as follows: `brew install zbar`.

You should be ready to run `sss.py` now! It can be invoked as a command line application, or imported as a library. Descriptions of each follow:

### CLI

- To view the CLI, run `python3 sss.py (-h | --help)`
- Two example invocations of `sss.py` via the command line are as follows:
    - Example 1: `python3 sss.py -s -m "Hello!" --enc_type "qr" 2 3`. Shares the message "Hello!" to 3 QR code shares with a recovery threshold of 2.
    - Example 2: `python3 sss.py --share -f message.txt --enc_type "base64" 3 5`. Shares the message whose contents lie in the file `message.txt` to 5 shares with a recovery threshold of 3.

### Interface (if imported as a library)
Pending!

