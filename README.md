DNS Update Plugin for Fuel
=======================

Overview 
--------------

DNS Update plugin for Fuel extends Mirantis OpenStack functionality by adding
support for configurable dns servers in murano virtual machines via notifications.

Compatible Fuel versions
--------------

9.0


User Guide
-------------

1. Create an environment.
2. Enable the plugin on the Settings/Other tab of the Fuel web UI and fill in form
    fields:
3. Deploy the environment.


DNS Update plugin installation
---------------------------

To install DNS Update plugin, follow these steps:

1. Download the plugin from
    [Fuel Plugins Catalog](https://software.mirantis.com/fuel-plugins)

2. Copy the plugin on already installed Fuel Master node; ssh can be used for
    that. If you do not have the Fuel Master node yet, see
    [Quick Start Guide](https://software.mirantis.com/quick-start/):

        # scp dns-update-1.0-1.0.0-0.noarch.rpm root@<Fuel_master_ip>:/tmp

3. Log into the Fuel Master node. Install the plugin:

        # cd /tmp
        # fuel plugins --install fuel-plugin-dns-update-1.0-1.0.0-0.noarch.rpm

4. Check if the plugin was installed successfully:

        # fuel plugins
        id | name                   | version | package_version
        ---|------------------------|---------|----------------
        1  | fuel-plugin-dns-update | 1.0.1   | 4.0.0

Requirements
------------

| Requirement                      | Version/Comment |
|:---------------------------------|:----------------|
| Mirantis OpenStack compatibility | 9.0             |
