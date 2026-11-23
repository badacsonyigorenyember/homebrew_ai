using HomebrewApp.Data;
using HomebrewApp.Features.Batches;

using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

using Npgsql;

namespace HomebrewApp.Tests.Database;

[Collection(nameof(ApiCollection))]
public class BatchTablesTests(ApiFactory factory)
{
    [Fact]
    public async Task Batch_WithItemAndStep_ReadsBackThroughAppDbContext()
    {
        long batchId;
        await using (var scope = factory.Services.CreateAsyncScope())
        {
            var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

            var recipe = await context.Recipes.FirstAsync();
            var batch = CreateBatch(501, recipe.Id);

            context.Batches.Add(batch);
            await context.SaveChangesAsync();
            batchId = batch.Id;
        }

        await using (var scope = factory.Services.CreateAsyncScope())
        {
            var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

            var result = await context.Batches
                .Include(b => b.Items)
                .Include(b => b.Steps)
                .SingleAsync(b => b.Id == batchId);

            Assert.Equal("Read back", result.Name);
            Assert.Single(result.Items);
            Assert.Equal("Test Item", result.Items.First().RawName);
            Assert.Single(result.Steps);
            Assert.Equal("Test Step", result.Steps.First().Title);
            Assert.NotEqual(DateTime.MinValue, result.CreatedAt);

            await context.Batches.Where(b => b.Id == result.Id).ExecuteDeleteAsync();
        }
    }

    [Fact]
    public async Task DeleteBatch_WithItemAndStep_DeletesThem()
    {
        await using var scope = factory.Services.CreateAsyncScope();
        var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        var recipe = await context.Recipes.FirstAsync();
        var batch = CreateBatch(502, recipe.Id);

        context.Batches.Add(batch);
        await context.SaveChangesAsync();

        await context.Batches.Where(b => b.Id == batch.Id).ExecuteDeleteAsync();

        Assert.Equal(0, await context.Batches.CountAsync(b => b.Id == batch.Id));
        Assert.Equal(0, await context.BatchItems.CountAsync(b => b.BatchId == batch.Id));
        Assert.Equal(0, await context.BatchSteps.CountAsync(b => b.BatchId == batch.Id));
    }

    [Fact]
    public async Task Batch_WithStatusOutsideThePhases_IsRefused()
    {
        await using var scope = factory.Services.CreateAsyncScope();
        var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        var recipe = await context.Recipes.FirstAsync();
        var batch = CreateBatch(503, recipe.Id, "brewing");

        context.Batches.Add(batch);

        var exception = await Assert.ThrowsAsync<DbUpdateException>(() => context.SaveChangesAsync());
        var typedException = Assert.IsType<PostgresException>(exception.InnerException);

        Assert.Equal(PostgresErrorCodes.CheckViolation, typedException.SqlState);
        Assert.Equal("batch_status_check", typedException.ConstraintName);
    }

    private static Batch CreateBatch(int number, long recipeId, string status = "plan")
    {
        return new Batch
        {
            Number = number,
            Name = "Read back",
            RecipeId = recipeId,
            BrewDate = new DateOnly(2026, 01, 01),
            Status = status,
            BatchL = 20,
            EfficiencyPct = 72,
            Process = "{}",
            Items =
            [
                new BatchItem
                {
                    RawName = "Test Item",
                    Usage = "mash",
                    Amount = 1,
                    Unit = "kg",
                    Changed = false
                }
            ],
            Steps =
            [
                new BatchStep
                {
                    Phase = "brew_day",
                    Position = 0,
                    Title = "Test Step",
                    Planned = "[]",
                    Actual = "{}",
                    DatePinned = false,
                    Source = "user"
                }
            ]
        };
    }
}
