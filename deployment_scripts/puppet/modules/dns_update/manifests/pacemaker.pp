class dns_update::pacemaker {
Exec { path => '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' }
$operations = {
    'monitor' => {'interval' => '5s', 'timeout' => '30s' },
    'start'   => {'interval' => '0s', timeout => '30s' },
    'stop'   => {'interval' => '0s', timeout => '30s' }
}

file {'DnsUpdater':
         path => '/usr/lib/ocf/resource.d/fuel/DnsUpdater',
         source => '/tmp/os_dns_updater/ocf/DnsUpdater',
       }

pacemaker::service { "DnsUpdater":
   primitive_class => 'ocf',
   primitive_provider => 'fuel',
   primitive_type => 'DnsUpdater',
   operations => $operations,
   use_handler => false,
   complex_type => 'clone',
}

service { "DnsUpdater":
   ensure => running,
   name => 'DnsUpdater',
   enable => true,
   provider => 'pacemaker'
}

exec {"Cleanup resources":
   command => "crm resource cleanup clone_p_DnsUpdater",
}

File['DnsUpdater'] ->
Service['DnsUpdater'] ->
Exec['Cleanup resources']

}
