class dns_update::mysql {
    $mysql_hash = hiera_hash('mysql')
    $mysql_pass = $mysql_hash['root_password']
    Exec { path => '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' }
    $dnsupdate_mysql_exist = inline_template("<% if File.exist?('/tmp/dnsupdate-mysql.lock') -%>true<% end -%>")

    if $dnsupdate_mysql_exist != 'true' {
    exec {"create dns_updater database":
           command => "mysql --host=localhost --user=root --password=$mysql_pass -e 'create database dnsupdate;'",
         } ->
    exec {"create dns_updater user":
           command => "mysql --host=localhost --user=root --password=$mysql_pass -e 'create user \"dnsupdate\"@\"%\" identified by \"ai2o3nvsjS3cvm\";'",
         } ->
    exec {"grant privileges to dns_updater user":
           command => "mysql --host=localhost --user=root --password=$mysql_pass -e 'grant all privileges on dnsupdate.* to \"dnsupdate\"@\"%\";'",
         } ->
    exec {"create tables":
         command => "python /tmp/os_dns_updater/db_setup.py",
    } ->
    file {"/tmp/dnsupdate-mysql.lock":
           path => "/tmp/dnsupdate-mysql.lock",
           ensure => "file",
    }
   }
}
