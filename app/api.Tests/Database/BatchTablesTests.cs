using HomebrewApp.Data;
using HomebrewApp.Features.Batches;

using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace HomebrewApp.Tests.Database;

[Collection(nameof(ApiCollection))]
public class BatchTablesTests(ApiFactory factory)
{
    [Fact]
    public async Task Batch_WithItemAndStep_ReadsBackThroughAppDbContext()
    {
        await using (var scope = factory.Services.CreateAsyncScope())
        {
            var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

            var recipeId = context.Recipes.FirstAsync().Id;

            var batch = new Batch
            {
                Number = 501,
                Name = "Read back",
                RecipeId = recipeId,
                BrewDate = new DateOnly(2026, 01, 01),
                Status = "plan",
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

            context.Batches.Add(batch);
            await context.SaveChangesAsync();
        }


        await using (var scope = factory.Services.CreateAsyncScope())
        {
            var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

            var result = await context.Batches
                .Include(b => b.Items)
                .Include(b => b.Steps)
                .SingleAsync();

            Assert.Equal("Read back", result.Name);
            Assert.Single(result.Items);
            Assert.Equal("Test Item", result.Items.First().RawName);
            Assert.Single(result.Steps);
            Assert.Equal("Test Step", result.Steps.First().Title);
            Assert.NotEqual(DateTime.MinValue, result.CreatedAt);

            await context.Batches.Where(b => b.Id == result.Id).ExecuteDeleteAsync();
        }
    }
}
