variable "region" { type = string }
variable "compartment_id" { type = string }
variable "availability_domain" { type = string }
variable "image_id" { type = string }
variable "admin_cidr" { type = string }
variable "subnet_id" {
  type        = string
  default     = ""
  description = "Existing subnet to use; empty creates the VASH network."
}
variable "ssh_public_key" { type = string }
variable "oci_auth" {
  type        = string
  default     = "ApiKey"
  description = "Provider auth: ApiKey (config file) or InstancePrincipal (Cloud Shell)."
}
variable "config_file_profile" {
  type    = string
  default = "DEFAULT"
}
variable "ocpus" {
  type    = number
  default = 2
}
variable "memory_in_gbs" {
  type    = number
  default = 12
}
variable "cloud_init_script" {
  type        = string
  default     = null
  description = "File name under scripts/ that the VM runs on first boot."
}
variable "create_database" {
  type    = bool
  default = false
}
variable "admin_password" {
  type      = string
  default   = ""
  sensitive = true
}
variable "name_prefix" {
  type        = string
  description = "Prefix of every display name this environment creates."
}
