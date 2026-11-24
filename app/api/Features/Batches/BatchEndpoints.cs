using System.ComponentModel.DataAnnotations;

using HomebrewApp.Data;

using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.EntityFrameworkCore;

namespace HomebrewApp.Features.Batches;

public record BatchSummaryResponse(
    long Id,
    int Number,
    string Name,
    string StyleCode,
    string? StyleName,
    DateOnly BrewDate,
    string Status);

public record CreateBatchRequest([Required] long? RecipeId, [Required] string? Name, [Required] DateOnly? BrewDate);

public record BatchResponse(
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
    List<BatchItemResponse> Items);

public record BatchItemResponse(
    long Id,
    long? SourceItemId,
    long? IngredientId,
    string RawName,
    string Usage,
    decimal? TimeMin,
    decimal? Percentage,
    decimal Amount,
    string Unit);

public static class BatchEndpoints
{
    public static IEndpointRouteBuilder MapBatchEndpoints(this IEndpointRouteBuilder endpoints)
    {
        var group = endpoints.MapGroup("/api/batches");

        group.MapGet("/", ListBatches);

        group.MapPost("/", CreateBatch)
            .ProducesValidationProblem()
            .ProducesProblem(StatusCodes.Status404NotFound);

        return endpoints;
    }

    private static async Task<Results<Created<BatchResponse>, ProblemHttpResult>> CreateBatch(
        CreateBatchRequest request,
        AppDbContext context,
        CancellationToken cancellationToken)
    {
        await using var transaction = await context.Database.BeginTransactionAsync(cancellationToken);

        var recipe = await context.Recipes.Include(r => r.Items)
            .SingleOrDefaultAsync(r => r.Id == request.RecipeId, cancellationToken);

        if (recipe is null)
        {
            return TypedResults.Problem("There is no recipe with id: " + request.RecipeId,
                statusCode: StatusCodes.Status404NotFound);
        }

        if (recipe.Process is null)
        {
            return TypedResults.Problem("The recipe has no process and so cannot be brewed.",
                statusCode: StatusCodes.Status400BadRequest);
        }

        var highestNumber = await context.Batches.MaxAsync(b => (int?)b.Number, cancellationToken);

        var batch = new Batch
        {
            Number = (highestNumber ?? 0) + 1,
            Name = request.Name!,
            BrewDate = request.BrewDate!.Value,
            RecipeId = recipe.Id,
            Status = "plan",
            BatchL = recipe.BatchL,
            EfficiencyPct = recipe.EfficiencyPct,
            Process = recipe.Process,
            OG = recipe.OG,
            FG = recipe.FG,
            ABV = recipe.ABV,
            IBU = recipe.IBU,
            SRM = recipe.SRM,
            Items =
            [
                .. recipe.Items.Select(i => new BatchItem
                {
                    SourceItemId = i.Id,
                    IngredientId = i.IngredientId,
                    RawName = i.RawName,
                    Usage = i.Usage,
                    TimeMin = i.TimeMin,
                    Percentage = i.Percentage,
                    Amount = i.Amount,
                    Unit = i.Unit,
                    Changed = false
                })
            ]
        };

        context.Batches.Add(batch);
        await context.SaveChangesAsync(cancellationToken);
        await transaction.CommitAsync(cancellationToken);

        var response = new BatchResponse(batch.Id, batch.Number, batch.Name, batch.RecipeId, batch.BrewDate,
            batch.Status, batch.BatchL, batch.EfficiencyPct, batch.OG, batch.FG, batch.ABV, batch.IBU, batch.SRM,
            [
                .. batch.Items.Select(i => new BatchItemResponse(i.Id, i.SourceItemId, i.IngredientId, i.RawName,
                    i.Usage, i.TimeMin, i.Percentage, i.Amount, i.Unit))
            ]);

        return TypedResults.Created($"/api/batches/{batch.Id}", response);
    }

    private static async Task<Ok<List<BatchSummaryResponse>>> ListBatches(
        AppDbContext context,
        CancellationToken cancellationToken)
    {
        var batches = await context.Batches.OrderByDescending(b => b.BrewDate)
            .ThenByDescending(b => b.Number)
            .Select(b => new BatchSummaryResponse(b.Id, b.Number, b.Name, b.Recipe.Style.Code,
                b.Recipe.Style.Name, b.BrewDate, b.Status))
            .ToListAsync(cancellationToken);

        return TypedResults.Ok(batches);
    }
}
