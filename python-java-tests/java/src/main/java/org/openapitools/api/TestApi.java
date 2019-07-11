package org.openapitools.api;

//import org.openapitools.model.*;
import org.openapitools.api.TestApiService;
import org.openapitools.api.factories.TestApiServiceFactory;

import io.swagger.annotations.ApiParam;
import io.swagger.jaxrs.*;

import java.math.BigDecimal;

import java.util.Map;
import java.util.List;
import org.openapitools.api.NotFoundException;

import java.io.InputStream;

import org.glassfish.jersey.media.multipart.FormDataContentDisposition;
import org.glassfish.jersey.media.multipart.FormDataParam;

import javax.servlet.ServletConfig;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.Response;
import javax.ws.rs.core.SecurityContext;
import javax.ws.rs.*;
import javax.validation.constraints.*;
import javax.validation.Valid;

@Path("/test")


@io.swagger.annotations.Api(description = "the test API")
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaJerseyServerCodegen", date = "2019-06-18T09:40:00.863+02:00[Europe/Paris]")
public class TestApi  {
   private final TestApiService delegate;

   public TestApi(@Context ServletConfig servletContext) {
      TestApiService delegate = null;

      if (servletContext != null) {
         String implClass = servletContext.getInitParameter("TestApi.implementation");
         if (implClass != null && !"".equals(implClass.trim())) {
            try {
               delegate = (TestApiService) Class.forName(implClass).newInstance();
            } catch (Exception e) {
               throw new RuntimeException(e);
            }
         } 
      }

      if (delegate == null) {
         delegate = TestApiServiceFactory.getTestApi();
      }

      this.delegate = delegate;
   }

    @GET
    @Path("/{value}")
    
    
    @io.swagger.annotations.ApiOperation(value = "Test", notes = "", response = Void.class, tags={  })
    @io.swagger.annotations.ApiResponses(value = { 
        @io.swagger.annotations.ApiResponse(code = 200, message = "Operation successful", response = Void.class) })
    public Response test(@ApiParam(value = "",required=true) @PathParam("value") BigDecimal value
,@Context SecurityContext securityContext)
    throws NotFoundException {
        return delegate.test(value,securityContext);
    }
}
