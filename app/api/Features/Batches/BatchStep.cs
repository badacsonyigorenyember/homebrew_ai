using System.ComponentModel.DataAnnotations.Schema;

namespace HomebrewApp.Features.Batches;

[Table("batch_step", Schema = "app")]
public class BatchStep
{
    [Column("id")]
    public long Id { get; init; }

    [Column("batch_id")]
    public long BatchId { get; init; }

    [Column("phase")]
    public required string Phase { get; init; }

    [Column("position")]
    public required int Position { get; init; }

    [Column("title")]
    public required string Title { get; init; }

    [Column("planned", TypeName = "jsonb")]
    public required string Planned { get; init; }

    [Column("actual", TypeName = "jsonb")]
    public required string Actual { get; init; }

    [Column("step_date")]
    public DateOnly? StepDate { get; init; }

    [Column("date_pinned")]
    public required bool DatePinned { get; init; }

    [Column("source")]
    public required string Source { get; init; }

    [Column("done_at")]
    public DateTime? DoneAt { get; init; }

    [Column("note")]
    public string? Note { get; init; }

    [Column("timer_started_at")]
    public DateTime? TimerStartedAt { get; init; }
}
