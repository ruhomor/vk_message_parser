cd ~/.wdm/drivers/geckodriver/macos
rm -rf "v0.29.1"
mkdir "v0.29.1"
cd ./v0.29.1
wget https://github.com/mozilla/geckodriver/releases/download/v0.29.1/geckodriver-v0.29.1-macos.tar.gz
tar xzf *.tar.gz
sudo xattr -dr com.apple.quarantine geckodriver
