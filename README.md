# Re-ReFrontier
Python rewrite and cleanup of original ReFrontier tool written by mhvuze and modified by Chakratos.
Original ReFrontier also ecxtends thank you to enler for their help!

Tools for *packing, *crypting and editing various Monster Hunter Frontier Online files.

Usage (WIP):
```
Unacking/Decryption:

Extracting Data/Exporting:

Packing/Encryption:
```

ReFrontier options (Writeup needs redone):
```
Unpacking Options:
-log: Write log file (required for repacking)
-cleanUp: Delete simple archives after unpacking
-stageContainer: Unpack file as stage-specific container (for certain stXXX.pac files and maybe others)
-autoStage: Automatically attempt to unpack containers that might be stage-specific (this is very experimental, since there is no reliable way to detect a stage-specific container)
-nonRecursive: Do not unpack recursively (useful for modifying specific files in archives, also check -noDecryption/-ignoreJPK)
-decryptOnly: Decrypt ecd files without unpacking
-noDecryption: Don't decrypt ecd files, no unpacking
-ignoreJPK: Do not decompress JPK files

Packing Options:
-pack: Repack directory (requires log file  - double check file extensions therein and make sure you account for encryption, compression)
-compress [type],[level]: Pack file with jpk [type] at compression [level] (example: -compress 3,10)
-encrypt: Encrypt input file with ecd algorithm

General Options:
-close: Close window after finishing process
```

Some more useful tools and projects:
- [Erupe - MHFO Server Hosting Tool](https://github.com/ZeruLight/Erupe)
- [MHFO Save Manager for Server Hosts](https://github.com/Chakratos/mhf-save-manager)
- [MHFO Quest Editor for Server Hosts](https://github.com/Chakratos/mhf-questfile-manager)
- [Wish's 101 Templates for MHFO](https://github.com/ZeruLight/010Templates)
- [MHFO Manual Mirror](https://github.com/ZeruLight/MHFZManual)