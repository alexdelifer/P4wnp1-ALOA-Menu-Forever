#!/bin/bash -e
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "${SCRIPT_DIR}/library/shared.sh"

echo "Install Luma.core drivers"
apt update --fix-missing
apt install -y python3-dev python3-pip \
    libfreetype6-dev libjpeg-dev \
    python3-luma.core python3-luma.oled \
    dsniff nmap

echo "Create directories"
mkdir -p "${LOOTDIR}"

echo "Updating Menu"
cd /root/ || exit 1
if [[ ! -d ${INSTALLDIR} ]]; then
    echo "${INSTALLDIR} does not exist, cloning now"
    git clone https://github.com/alexdelifer/P4wnp1-ALOA-Menu-Forever.git /root/DeliMenu

else
    "${INSTALLDIR}/update.sh"
fi

echo "Updating Service"
cd "${INSTALLDIR}" || exit 6
cp "service/P4wnP1_oledmenu.service" "/etc/systemd/system/P4wnP1_oledmenu.service"
systemctl daemon-reload
systemctl enable --now P4wnP1_oledmenu.service

