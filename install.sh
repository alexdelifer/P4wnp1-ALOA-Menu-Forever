#!/bin/bash -e
echo "Install Luma.core drivers"
apt update --fix-missing
apt install -y python3-dev python3-pip \
    libfreetype6-dev libjpeg-dev \
    python3-luma.core python3-luma.oled \
    dsniff nmap

echo "Create directories"
#mkdir -p /root/DeliMenu/{images,nmap}
mkdir -p /usr/local/P4wnP1/www/loot/DeliMenu

echo "Updating Menu"
cd /root/ || exit 1
INSTALLDIR="/root/DeliMenu"
if [[ ! -d ${INSTALLDIR} ]]; then
    echo "${INSTALLDIR} does not exist, cloning now"
    git clone https://github.com/alexdelifer/P4wnp1-ALOA-Menu-Forever.git /root/DeliMenu

else
    cd "${INSTALLDIR}" || exit 2
    git stash || exit 3
    git pull || exit 4
    git stash pop || exit 5

fi

echo "Updating Service"
cd "${INSTALLDIR}" || exit 6
cp "service/P4wnP1_oledmenu.service" "/etc/systemd/system/P4wnP1_oledmenu.service"
systemctl daemon-reload
systemctl enable --now P4wnP1_oledmenu.service

