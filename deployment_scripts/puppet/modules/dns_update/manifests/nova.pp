class dns_update::nova {

  $nova_compute_exist = inline_template("<% if File.exist?('/etc/init.d/nova-compute') -%>true<% end -%>")
  $nova_api_exist = inline_template("<% if File.exist?('/etc/init.d/nova-api') -%>true<% end -%>")

  nova_config {
    "DEFAULT/dhcp_domain": value => "vm.example.net";
  }

  if $nova_compute_exist == "true"
  {
    Nova_config <||> ~> service { 'nova-compute': }
  }

  if $nova_api_exist == "true"
  {
    Nova_config <||> ~> service { 'nova-api': }
  }
}
