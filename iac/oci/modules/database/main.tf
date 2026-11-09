terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0"
    }
  }
}

resource "oci_database_autonomous_database" "db" {
  compartment_id           = var.compartment_id
  db_name                  = substr(replace("${var.name_prefix}db", "-", ""), 0, 14)
  display_name             = "${var.name_prefix}-db"
  cpu_core_count           = 1
  data_storage_size_in_tbs = 1
  db_workload              = "OLTP"
  is_free_tier             = true
  admin_password           = var.admin_password
}
