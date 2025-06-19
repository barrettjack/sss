## Shamir secret sharing library + standalone application written in python.

### **DISCLAIMER:**
**I am not a cybersecurity expert, nor am I a cryptography expert. I make absolutely no guarentees about the correctness or security of the implementation provided here. As such, I take no responsibility for losses incurred as a result of using this library/app. Don't roll your own crypto, as they say... You have been warned with abundant clarity and in no uncertain terms!**

### Motivation

I thought it would be fun to play around with implementing Shamir's secret sharing scheme in python, having learned about the scheme in UVic's course on cryptography. It is a simple and elegant (yet secure) scheme, which I invite you to appreciate by:

- checking out the post I made on my personal site detailing the mathematics of the scheme.
- reading the source code!

### Practical utility

The practical utility of this scheme is that it provides a means to "break down" a key into shares without comprimising the security of the key that the shares protect. More concretely, you could take a key you wish to protect (say the backup key for your password manager) and split it into 3 shares such that:
- 2 of the 3 shares are required to recover the key.
- an attacker is in no better a position with 1 share than he is with 0 shares. (If an attacker comprimizes only one of your shares, he cannot recover the key.)

### Interface (if imported as a library)

### CLI description (if invoked as a standalone application)


