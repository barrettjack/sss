## Shamir secret sharing library + standalone application written in python.

### **DISCLAIMER:**
**I am not a cybersecurity expert, nor am I a cryptography expert. I make absolutely no guarentees about the correctness or security of the implementation provided here. As such, I take no responsibility for losses incurred as a result of using this library/app. Don't roll your own crypto, as they say... You have been warned with abundant clarity and in no uncertain terms!**

### Motivation

I thought it would be fun to play around with implementing Shamir's secret sharing scheme in python, having learned about the scheme in UVic's course on cryptography. It is a simple and elegant (yet secure) scheme, which I invite you to appreciate by checking out the source code, and/or by reading about the scheme on [Wikipedia](https://en.wikipedia.org/wiki/Shamir%27s_secret_sharing).

### Practical utility

The practical utility of this scheme is that it provides a means to "break down" a key into shares without comprimising the security of the key that the shares protect. More concretely, you could take a key you wish to protect (say the backup key for your password manager) and split it into 3 shares such that:
- 2 of the 3 shares are required to recover the key.
- an attacker is in no better a position with 1 share than he is with 0 shares. (If an attacker comprimizes fewer than the threshold number of shares, he has not learned any information about the key.)

### Setup
- Here will go a description of the setup required to get this library/app working (the user shouldn't have to think about this, particularly if invoking the app via the CLI!)
- Setup requirements.txt and ship in the repo
- Can I get python to install all the requirements on invoking this program? I think that should be possible...
-Add a remark about homebrew and zbar is running on mac

### Interface (if imported as a library)

### CLI description (if invoked as a standalone application)
- `python3 sss.py (-s | --share) (-m | -f) (message | filename) --enc_type ("base64" | "qr") threshold number_of_shares`
    - This form of invocation can be used to share a message with threshold `threshold`, yielding `number_of_shares` shares.
    - Example 1: `python3 sss.py -s -m "Hello!" --enc_type "qr" 2 3`
    - Example 2: `python3 sss.py --share -f message.txt 3 5`
- `python3 sss.py (-r | --reconstruct) --enc_type ("base64" | "qr") (path_to_base64_encoded_shares | path_to_qr_codes)`
    - This form of invocation is used to attempt to reconstruct a message from a set of shares.


