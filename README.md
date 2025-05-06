# Civit-Model-Archiver
Firstly, this started as a fork of [CivitAI-Model-grabber](https://github.com/Confuzu/CivitAI-Model-grabber) to add the ability to export a single mode. but then my changes got a bit out of hand. Big thank you to [Confuzu](https://github.com/Confuzu/CivitAI-Model-grabber/commits?author=Confuzu) for the original code, thank you!

The script Supports different download types: Lora, Checkpoints, Embeddings for a given model or all models for a bunch of usernames or model ids or both.

It's designed to download only the files that are not already present in the specified username's folder.
If the user uploads new models, running the script again will download only the newly uploaded files.

This runs a SHA256 on all downloaded models to ensure the file is complete and matches the hash proivded by CivitAI

The code is a bit rough, it has been a rushed a bit to meet the deadline for the recent content removal due to TOS changes.


**File Structure**  <br /> 
The downloaded files will be organized in the following structure:
```
model_downloads/
├── User Name/
│   └── [Model Name] ([Model Type])/
│       ├── [Model Id].json 
│       ├── description.html 
│       ├── [Model Version] ([Base Model])/
│       │       ├── file1.safetensors
│       │       ├── image1.jpeg
│       │       ├── details.txt
│       │       ├── trained_works.txt
│       │       └── description.html
│       └── [Model Version] ([Base Model])/
│               ├── file3.safetensors
│               ├── image2.jpeg
│               ├── details.txt
│               ├── triggerWords.txt
│               └── description.html
└── User Name/
    └── ...
```

# Install

### local deps
```
install Python3
```
```
pip install -r requirements.txt
```

#### or virtual env:
```
python3 -m venv vvv
source vvv/bin/activate
pip install -r requirements.txt
```

# How to use

Download models:
```
python archive_model.py --models 1 2 3 4
```

Download all models for user:
```
python archive_model.py --usernames UserName1 UserName2
```

Download both
```
python archive_model.py --usernames UserName1 UserName2 --models 1 2 3 4
```


#### Required Arguments:
```
--models 1 2 3 4 5 6
```
+ "A list of model ids taken from the URL of the model view page on CivitAI"
```
--usernames username1 username2
```
+ "A list of usernames from CivitAI"
```
--token 
```
default=None
+ "It will only Download the Public availabe Models"
+ "Provide a Token and it can also Download those Models behind the CivitAI Login."
+ If you forgot to Provide a Token the Script asks for your token.


#### Optional Arguments:
```
You can also give the script this 5 extra Arguments
```

--only_base_models
```
+ default=,
+ "Filter model version by the base model they are built on (SDXL, SD 1.5, Pony, Flux, ETC) see readme for list."
+ example: --only_base_models "SD 1.4" "SD 2.0" "SD 3.5"
```

Some examples:
| Base Models      
| :---------------- 
| `SD 1.4`
| `SD 1.5`
| `SD 1.5 LCM`
| `SD 1.5 Hyper`
| `SD 2.0`
| `SD 2.0 768`
| `SD 2.1`
| `SD 2.1 768`
| `SD 2.1 Unclip`
| `SDXL 0.9`
| `SDXL 1.0`
| `SD 3`
| `SD 3.5`
| `SD 3.5 Medium`
| `SD 3.5 Large`
| `SD 3.5 Large Turbo`
| `Pony`
| `Flux.1 S`
| `Flux.1 D`
| `AuraFlow`
| `SDXL 1.0 LCM`
| `SDXL Distilled`
| `SDXL Turbo`
| `SDXL Lightning`
| `SDXL Hyper`
| `Stable Cascade`
| `SVD`
| `SVD XT`
| `Playground v2`
| `PixArt a`
| `PixArt E`
| `Hunyuan 1`
| `Hunyuan Video`
| `Lumina`
| `Kolors`
| `Illustrious`
| `Mochi`
| `NSFW MASTER FLUX`
| `LTXV`
| `CogVideoX`
| `NoobAI`
| `Wan Video`
| `HiDream`
| `Other`




--retry_delay 
```
+ default=10,
+ "Retry delay in seconds."
```

--max_tries
```
+ default=5,
+ "Maximum number of retries."
```

--max_threads
```
 + default=5, 
 + "Maximum number of concurrent threads.Too many produces API Failure."
```

--max_threads
```
 + default=model_archives, 
 + "The place to output the downloads, defaults to 'model_archives'."
```

--skip_existing_verification
```
 + default=false, 
 + "Skip SHA256 verification of existing downloads."
```

--skip_compress_models
```
 + default=false, 
 + "Skip compressing model files with 7 Zip."
```


#### Setup:
You can create your API Key here
 [Account Settings](https://civitai.com/user/account).
 Scoll down until  the end and you  find this Box

![API](https://github.com/RtypeStudios/CivitAI-Model-Archiver/raw/refs/heads/main/api_login_example.png)


# Alternatives:
- [A powerful go based downloader, with DB functionality and filter](https://github.com/dreamfast/go-civitai-downloader)

# Updates & Bugfixes
coming soon ...


