output "runner_ip" { value = data.oci_core_vnic.runner.public_ip_address }
output "instance_id" { value = module.instance.instance_tf_id }
output "db_id" { value = var.create_database ? module.database[0].db_id : null }
