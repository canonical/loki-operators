output "app_names" {
  value = merge(
    {
      loki_s3_integrator = juju_application.s3_integrator.name,
      loki_coordinator   = module.loki_coordinator.app_name,
      loki_backend       = module.loki_backend.app_name,
      loki_read          = module.loki_read.app_name,
      loki_write         = module.loki_write.app_name,
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
    provide_cmr_mesh            = module.loki_coordinator.provides.provide_cmr_mesh,
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
    require_cmr_mesh = module.loki_coordinator.provides.require_cmr_mesh,
    service_mesh     = module.loki_coordinator.provides.service_mesh,
  }
  description = "All Juju integration endpoints where the charm is the requirer"
}
