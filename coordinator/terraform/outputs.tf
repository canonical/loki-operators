output "app_name" {
  value = juju_application.loki_coordinator.name
}

output "provides" {
  value = {
    loki_cluster = "loki-cluster"
  }
  description = "All Juju integration endpoints where the charm is the provider"
}

output "requires" {
  value = {}
  description = "All Juju integration endpoints where the charm is the requirer"
}
