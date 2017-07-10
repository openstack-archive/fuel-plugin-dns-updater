class dns_update::neutron {

Exec { path => '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' }
$neutron_adv_con=hiera('neutron_advanced_configuration')
$ha=$neutron_adv_con['dhcp_agent_ha']
$neutron_dhcp_exist = inline_template("<% if File.exist?('/etc/init.d/neutron-dhcp-agent') -%>true<% end -%>")

  neutron_config {
       "DEFAULT/dns_domain": value => "vm.example.net";
  }
  if $neutron_dhcp_exist == "true" {
     neutron_dhcp_agent_config {
          "DEFAULT/dhcp_domain": value => "vm.example.net";
     }
     if ($ha == true) {
        exec{"neutron-dhcp-agent crm restart":
              command => "crm resource restart clone_neutron-dhcp-agent",
        }
        Neutron_config <||> ~> Exec['neutron-dhcp-agent crm restart']
        Neutron_dhcp_agent_config <||> ~> Exec['neutron-dhcp-agent crm restart']
     }
     elsif ($ha == false) {
        exec{"neutron-dhcp-agent service restart":
              command => "service neutron-dhcp-agent restart",
        }
        Neutron_config <||> ~> Exec['neutron-dhcp-agent service restart']
        Neutron_dhcp_agent_config <||> ~> Exec['neutron-dhcp-agent service restart']
     }
  }
Neutron_config <||> ~> service { 'neutron-server': }
}
