using HomebrewApp.Data;

using Microsoft.AspNetCore.Http.HttpResults;

namespace HomebrewApp.Features.Health;

public record HealthResponse(string Status, string Database);

public static class HealthEndpoints
{
    public static IEndpointRouteBuilder MapHealthEndpoint(this IEndpointRouteBuilder endpoints)
    {
        endpoints.MapGet("/api/health", HandleHealthCheck);
        return endpoints;
    }

    private static async Task<Ok<HealthResponse>> HandleHealthCheck(AppDbContext dbContext,
        CancellationToken cancellationToken)
    {
        var canConnectToDb = await dbContext.Database.CanConnectAsync(cancellationToken);
        var response = new HealthResponse("ok", canConnectToDb ? "ok" : "down");
        return TypedResults.Ok(response);
    }
}
