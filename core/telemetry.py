from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging
from fastapi_app.core.config import settings

def enable_telemetry():
    if settings.azure_appinsights_key:
        logger = logging.getLogger()
        logger.addHandler(AzureLogHandler(
            connection_string=f'InstrumentationKey={settings.azure_appinsights_key}'
        ))
        logger.info("Azure Application Insights telemetry enabled.")
