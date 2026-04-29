output "app_names" {
  value = merge(
    {
      loki_s3_integrator = var.deploy_s3_integrator ? juju_application.s3_integrator[0].name : null,
      loki_coordinator   = module.loki_coordinator.app_name,
      loki_all           = var.monolithic ? module.loki_all[0].app_name : null,
      loki_backend       = var.monolithic ? null : module.loki_backend[0].app_name,
      loki_read          = var.monolithic ? null : module.loki_read[0].app_name,
      loki_write         = var.monolithic ? null : module.loki_write[0].app_name,
    }
  )
  description = "All application names which make up this product module"
}

output "provides" {
  value = {
    grafana_dashboards_provider = "grafana-dashboards-provider",
    grafana_source              = "grafana-source",
    logging                     = "logging",
    loki_cluster                = module.loki_coordinator.provides.loki_cluster,
    receive_remote_write        = "receive-remote-write",
    self_metrics_endpoint       = "self-metrics-endpoint",
    send_datasource             = "send-datasource",
  }
  description = "All Juju integration endpoints where the charm is the provider"
}

output "requires" {
  value = {
    alertmanager     = "alertmanager",
    certificates     = "certificates",
    ingress          = "ingress",
    logging_consumer = "logging-consumer",
    s3               = "s3",
    charm_tracing    = "charm-tracing",
  }
  description = "All Juju integration endpoints where the charm is the requirer"
}
