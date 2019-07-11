package org.openapitools.api;

import org.openapitools.api.*;
//import org.openapitools.model.*;

import org.glassfish.jersey.media.multipart.FormDataContentDisposition;

import java.math.BigDecimal;

import java.util.List;
import org.openapitools.api.NotFoundException;

import java.io.InputStream;

import javax.ws.rs.core.Response;
import javax.ws.rs.core.SecurityContext;
import javax.validation.constraints.*;
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaJerseyServerCodegen", date = "2019-06-18T09:40:00.863+02:00[Europe/Paris]")
public abstract class TestApiService {
    public abstract Response test(BigDecimal value,SecurityContext securityContext) throws NotFoundException;
}
