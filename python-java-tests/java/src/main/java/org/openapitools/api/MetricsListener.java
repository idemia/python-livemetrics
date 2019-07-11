
package org.openapitools.api;

import com.codahale.metrics.*;
import com.codahale.metrics.servlets.*;

public class MetricsListener extends MetricsServlet.ContextListener {

    public static final MetricRegistry METRIC_REGISTRY = new MetricRegistry();

    @Override
    protected MetricRegistry getMetricRegistry() {
        return METRIC_REGISTRY;
    }

}