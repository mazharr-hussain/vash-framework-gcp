variable "compartment_id" { type = string }
variable "admin_password" {
  type      = string
  sensitive = true
}
variable "name_prefix" {
  type = string
}
