using Microsoft.AspNetCore.Http.HttpResults;

namespace HomebrewApp.Features.Health;

public record HealthResponse(string Status);

public static class HealthEndpoints
{
    public static IEndpointRouteBuilder MapHealthEndpoint(this IEndpointRouteBuilder endpoints)
    {
        endpoints.MapGet("/api/health", HandleHealthCheck);
        return endpoints;
    }

    private static Ok<HealthResponse> HandleHealthCheck()
    {
        var response = new HealthResponse("ok");
        return TypedResults.Ok(response);
    }
}
