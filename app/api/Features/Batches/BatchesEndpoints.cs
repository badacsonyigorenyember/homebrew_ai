using System.ComponentModel.DataAnnotations;

using HomebrewApp.Data;

using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.EntityFrameworkCore;

namespace HomebrewApp.Features.Batches;

public static class BatchesEndpoints
{
    public record BatchResponse(
        long Id,
        int Number,
        string Name,
        string StyleCode,
        string? StyleName,
        DateOnly BrewDate,
        string Status);

    public record Request([Required] long? RecipeId, [Required] string? Name, [Required] DateOnly? BrewDate);

    public record Response(
        long Id,
        int Number,
        string Name,
        long RecipeId,
        DateOnly BrewDate,
        string Status,
        decimal BatchL,
        decimal EfficiencyPct,
        decimal? OG,
        decimal? FG,
        decimal? ABV,
        decimal? IBU,
        decimal? SRM,
        List<ItemResponse> Items);

    public record ItemResponse(
        long Id,
        long? SourceItemId,
        long? IngredientId,
        string RawName,
        string Usage,
        decimal? TimeMin,
        decimal? Percentage,
        decimal Amount,
        string Unit);

    public static IEndpointRouteBuilder MapBatchesEndpoints(this IEndpointRouteBuilder endpoints)
    {
        endpoints.MapGroup("/api/batches")
            .MapGet("/", GetBatches);
        return endpoints;
    }

    private static async Task<Ok<List<BatchResponse>>> GetBatches(
        AppDbContext dbContext,
        CancellationToken cancellationToken)
    {
        var batches = await dbContext.Batches.OrderByDescending(b => b.BrewDate)
            .ThenByDescending(b => b.Number)
            .Select(b => new BatchResponse(b.Id, b.Number, b.Name, b.Recipe.Style.Code,
                b.Recipe.Style.Name, b.BrewDate, b.Status))
            .ToListAsync(cancellationToken);

        return TypedResults.Ok(batches);
    }
}
