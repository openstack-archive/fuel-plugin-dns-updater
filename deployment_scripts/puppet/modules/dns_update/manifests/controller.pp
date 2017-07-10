class dns_update::controller {
$plugin_hash      = hiera('fuel-plugin-dns-update')
$amqp_hosts = hiera('amqp_hosts')
$net1 = $plugin_hash['net1']
$net2 = $plugin_hash['net2']
$dns_key_hash=$plugin_hash['dns_key']
$dns_key=$dns_key_hash['content']
$rabbit_hash = hiera_hash('rabbit')
$amqp_user = $rabbit_hash['user']
$amqp_password = $rabbit_hash['password']
$node_hash = hiera('node')
$node_net = $node_hash['network_roles']
$node_management = $node_net['management']
$dnsupdate_mysql_exist = inline_template("<% if File.exist?('/tmp/dnsupdate-mysql.lock') -%>true<% end -%>")

if $management_vip == $service_endpoint { #in case of local keystone
  $region='RegionOne'
}
else { #in case of detach keystone
  $region=hiera(region)
}

Exec { path => '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' }

file {'os_dns_updater':
         path => '/tmp/os_dns_updater',
         source => 'puppet:///modules/dns_update/',
         recurse => 'true',
       }

package {'python-pip':
  ensure => 'installed',
}

package {'python-dnspython':
  ensure => 'installed',
}

package {'python-pymysql':
  ensure => 'installed'
}
package {'pycrypto':
  ensure => 'installed',
  provider => 'pip',
}
  file {'/etc/os_dns_updater':
         ensure => 'directory',
       }
  if $dnsupdate_mysql_exist != 'true' {
     exec {"install dns_updater":
          command  => "pip install -e /tmp/os_dns_updater/",
          require  => File['os_dns_updater'],
     }
  }
  file {'openstack-dns-updater.conf':
         path => '/etc/os_dns_updater/dns-updater.conf',
         source => 'puppet:///modules/dns_update/etc/dns-updater.conf',
         require => File['/etc/os_dns_updater'],
       }
  file {'example.key':
         path => '/etc/os_dns_updater/exaple.key',
         content => $dns_key,
         require => File['/etc/os_dns_updater'],
       }
file_line { "vm networks configuration":
    path => "/etc/os_dns_updater/dns-updater.conf",
    line => "networks=$net1,$net2",
    match => "networks=.*",
    require => File['openstack-dns-updater.conf'],
}
file_line { "region configuration":
    path => "/etc/os_dns_updater/dns-updater.conf",
    line => "region=$region",
    match => "region=.*",
    require => File['openstack-dns-updater.conf'],
}
file_line { "amqp host configuration":
    path => "/etc/os_dns_updater/dns-updater.conf",
    line => "amqp_hosts=$amqp_hosts",
    match => "amqp_hosts=.*",
    require => File['openstack-dns-updater.conf'],
}
file_line { "amqp password configuration":
    path => "/etc/os_dns_updater/dns-updater.conf",
    line => "amqp_password=$amqp_password",
    match => "amqp_password=.*",
    require => File['openstack-dns-updater.conf'],
}
file_line { "amqp user configuration":
    path => "/etc/os_dns_updater/dns-updater.conf",
    line => "amqp_user=$amqp_user",
    match => "amqp_user=.*",
    require => File['openstack-dns-updater.conf'],
}

  file {'added module to dist-packages':
         path => '/usr/lib/python2.7/dist-packages/os_dns_updater',
         source => '/tmp/os_dns_updater/os_dns_updater',
         recurse => 'true',       
       }
File['os_dns_updater']->
Package['python-pip']->
Package['python-pymysql']->
Package['pycrypto']->
File['/etc/os_dns_updater']

}
