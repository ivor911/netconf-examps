systemctl stop netopeer2-server
systemctl stop rbbn-nos-host_hooks
systemctl stop flex-cdcknet-config
systemctl stop flex-coctdsp-config
systemctl stop flex-cmand-config
systemctl stop flex-csipua-config
systemctl stop flex-csipgw-config
systemctl stop flex-csippri-config

systemctl --install ./oven.yang
sysrepocfg --import=./oven-default.xml -d running -m oven
#sysrepocfg  --edit=vim -d running -m oven

systemctl restart netopeer2-server

./oven.py

netopeer2-cli
> connect --host localhost --login root
> get --filter-xpath /oven:oven-state
> user-rpc --content oven-insert-food.xml
> user-rpc --content oven-remove-food.xml
