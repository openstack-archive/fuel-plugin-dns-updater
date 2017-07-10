class dns_update::service {

Exec { path => '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' }

  file {'init openstack-dns-updater.conf':
         path => '/etc/init/openstack-dns-updater.conf',
         source => '/tmp/os_dns_updater/openstack-dns-updater.conf',
       }

exec{"start openstack-dns-updater":
     command => "service openstack-dns-updater start",
     require => File['init openstack-dns-updater.conf'],
     returns => [0,1],
}

}
