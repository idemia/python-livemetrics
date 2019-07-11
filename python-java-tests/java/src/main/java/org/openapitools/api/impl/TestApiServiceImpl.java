package org.openapitools.api.impl;

import org.openapitools.api.*;
//import org.openapitools.model.*;

import java.math.BigDecimal;

import java.util.List;
import org.openapitools.api.NotFoundException;

import java.io.InputStream;

import org.glassfish.jersey.media.multipart.FormDataContentDisposition;

import javax.ws.rs.core.Response;
import javax.ws.rs.core.SecurityContext;
import javax.validation.constraints.*;

import com.codahale.metrics.*;


@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaJerseyServerCodegen", date = "2019-06-18T09:40:00.863+02:00[Europe/Paris]")
public class TestApiServiceImpl extends TestApiService {
    @Override
    public Response test(BigDecimal value, SecurityContext securityContext) throws NotFoundException {

        MetricRegistry metrics = MetricsListener.METRIC_REGISTRY;
        Meter requests = metrics.meter("requests");
        requests.mark();

        Histogram counts = metrics.histogram("values");
        counts.update(value.longValue());

        // do some magic!
        return Response.ok().entity(new ApiResponseMessage(ApiResponseMessage.OK, "magic!")).build();
    }
}
