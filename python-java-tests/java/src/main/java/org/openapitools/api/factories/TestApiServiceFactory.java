package org.openapitools.api.factories;

import org.openapitools.api.TestApiService;
import org.openapitools.api.impl.TestApiServiceImpl;

@javax.annotation.Generated(value = "org.openapitools.codegen.languages.JavaJerseyServerCodegen", date = "2019-06-18T09:40:00.863+02:00[Europe/Paris]")
public class TestApiServiceFactory {
    private final static TestApiService service = new TestApiServiceImpl();

    public static TestApiService getTestApi() {
        return service;
    }
}
